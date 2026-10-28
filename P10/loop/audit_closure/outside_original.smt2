; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x17 ((_ extract 15 0) c)))
(let ((?x18 (bvadd ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ extract 15 0) b))) ?x17)))
(let (($x19 (and (distinct (ite (bvult a (_ bv8 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x20 (ite $x19 ?x18 c)))
(and (not (bvult a (_ bv8 16))) (and (distinct ?x20 c) true)))))))
(check-sat)
