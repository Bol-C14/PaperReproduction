; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x41 (bvmul ((_ zero_extend 6) ((_ extract 1 0) ((_ extract 7 0) b))) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) a))))))
(let (($x5 (and (distinct (ite (bvult b (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x13 (ite $x5 (bvadd ((_ extract 7 0) ((_ extract 7 0) (_ bv1 8))) ((_ extract 7 0) ((_ extract 7 0) ?x41))) c)))
(let (($x25 (and (distinct (ite (bvult a (_ bv8 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x26 (ite $x5 (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ extract 7 0) b))) ((_ extract 7 0) (_ bv1 8))) c)))
(and (distinct (ite $x25 ?x26 c) (ite $x25 ((_ extract 7 0) ?x13) c)) true)))))))
(check-sat)
