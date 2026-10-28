; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x116 (bvmul ((_ zero_extend 14) ((_ extract 1 0) ((_ extract 15 0) b))) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a))))))
(let (($x61 (and (distinct (ite (bvult b (_ bv4 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x57 (ite $x61 (bvadd ((_ extract 15 0) ((_ extract 15 0) ?x116)) ((_ extract 15 0) ((_ extract 15 0) (_ bv1 16)))) c)))
(let (($x32 (and (distinct (ite (bvult a (_ bv8 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x9 (ite $x61 (bvadd ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ extract 15 0) b))) ((_ extract 15 0) (_ bv1 16))) c)))
(and (distinct (ite $x32 ?x9 c) (ite $x32 ?x57 c)) true)))))))
(check-sat)
